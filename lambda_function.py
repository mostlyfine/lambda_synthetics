import time
import logging
import aiohttp
import asyncio
import boto3
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

logger = logging.getLogger(__name__)


async def fetch(session, url, timeout, headers):
    start_time = time.time()
    try:
        async with session.get(url, timeout=timeout, headers=headers) as response:
            duration = time.time() - start_time
            status_code = response.status
            return url, status_code, duration
    except asyncio.TimeoutError:
        duration = time.time() - start_time
        return url, 504, duration  # Gateway Timeout
    except Exception as e:
        logger.error(f"Failed to fetch {url} {e}")
        duration = time.time() - start_time
        return url, str(e), duration


async def on_request_start(session, trace_config_ctx, params):
    logger.debug(f'Start request: {params.url.host}:{params.url.port}')


async def on_request_end(session, trace_config_ctx, params):
    logger.debug(f'End request: {params.url.host}:{params.url.port} "{params.method} {params.url.path} {params.response.status}"')


async def main(urls, timeout, concurrency, headers):
    trace_config = aiohttp.TraceConfig()
    trace_config.on_request_start.append(on_request_start)
    trace_config.on_request_end.append(on_request_end)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=concurrency), trace_configs=[trace_config]) as session:
        tasks = [fetch(session, url, timeout, headers) for url in urls]
        responses = await asyncio.gather(*tasks)
        return responses


def push_metrics_to_gateway(pushgateway_url, responses):
    region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    registry = CollectorRegistry()
    for url, status_code, duration in responses:
        response_time_gauge = Gauge('url_response_time_seconds', 'Response time for URL', ['url'], registry=registry)
        status_code_gauge = Gauge('url_status_code', 'Status code for URL', ['url'], registry=registry)
        response_time_gauge.labels(url=url, region=region).set(duration)
        status_code_gauge.labels(url=url, region=region).set(int(status_code) if isinstance(status_code, int) else 0)
    push_to_gateway(pushgateway_url, job='url_monitoring', registry=registry)


def put_metrics_to_cloudwatch(responses):
    region = os.getenv("AWS_DEFAULT_REGION", "ap-northeast-1")
    cloudwatch = boto3.client('cloudwatch', region_name=region)
    for url, status_code, duration in responses:
        try:
            response = cloudwatch.put_metric_data(
                Namespace='Synthetics',
                MetricData=[
                    {
                        'MetricName': 'ResponseTime',
                        'Dimensions': [
                            {
                                'Name': 'URL',
                                'Value': url
                            },
                            {
                                'Name': 'Region',
                                'Value': region
                            }
                        ],
                        'Value': duration,
                        'Unit': 'Seconds'
                    },
                    {
                        'MetricName': 'StatusCode',
                        'Dimensions': [
                            {
                                'Name': 'URL',
                                'Value': url
                            },
                            {
                                'Name': 'Region',
                                'Value': region
                            }
                        ],
                        'Value': status_code,
                        'Unit': 'Count'
                    }
                ]
            )
            logger.debug(response)
        except (NoCredentialsError, PartialCredentialsError):
            logger.error("AWS credentials not found.")
        except Exception as e:
            logger.error(f"Failed to put metric data: {e}")


def lambda_handler(event, context):
    logger.info(event)
    urls = event.get('urls', [])
    timeout = event.get('timeout', 10)
    concurrency = event.get('concurrency', 10)
    headers = event.get('headers', {})
    pushgateway_url = event.get('pushgateway_url', '')
    put_cw = event.get('cloudwatch', False)

    loop = asyncio.get_event_loop()
    responses = loop.run_until_complete(main(urls, timeout, concurrency, headers))

    if pushgateway_url:
        push_metrics_to_gateway(pushgateway_url, responses)

    if put_cw:
        put_metrics_to_cloudwatch(responses)

    logger.info(responses)

    return {
        'statusCode': 200,
        'body': 'successfully'
    }

