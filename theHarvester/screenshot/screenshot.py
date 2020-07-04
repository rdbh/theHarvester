"""
Screenshot module that utilizes pyppeteer to asynchronously
take screenshots
"""

from pyppeteer import launch
import aiohttp
import asyncio
from datetime import datetime
import json
import sys


class ScreenShotter:

    def __init__(self, output):
        self.output = output
        self.slash = "\\" if 'win' in sys.platform else '/'
        self.slash = "" if (self.output[-1] == "\\" or self.output[-1] == "/") else self.slash

    @staticmethod
    async def verify_installation():
        # Helper function that verifies pyppeteer & chromium are installed
        # If chromium is not installed pyppeteer will prompt user to install it
        browser = await launch(headless=True, ignoreHTTPSErrors=True, args=["--no-sandbox"])
        await browser.close()

    @staticmethod
    def chunk_list(items, chunk_size):
        # Based off of: https://github.com/apache/incubator-sdap-ingester
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

    @staticmethod
    async def visit(url):
        try:
            # print(f'attempting to visit: {url}')
            timeout = aiohttp.ClientTimeout(total=35)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                     'Chrome/83.0.4103.106 Safari/537.36'}
            url = f'http://{url}' if ('http' not in url and 'https' not in url) else url
            url = url.replace('www.', '')
            async with aiohttp.ClientSession(timeout=timeout, headers=headers,
                                             connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.get(url) as resp:
                    # TODO fix with origin url, should be there somewhere
                    text = await resp.text("UTF-8")
                    return f'http://{url}' if ('http' not in url and 'https' not in url) else url, text
        except Exception as e:
            print(f'An exception has occurred while attempting to visit {url} : {e}')
            return "", ""

    async def take_screenshot(self, url):
        url = f'http://{url}' if ('http' not in url and 'https' not in url) else url
        url = url.replace('www.', '')
        print(f'Attempting to take a screenshot of: {url}')
        browser = await launch(headless=True, ignoreHTTPSErrors=True, args=["--no-sandbox"])
        context = await browser.createIncognitoBrowserContext()
        page = await browser.newPage()
        path = fr'{self.output}{self.slash}{url.replace("http://", "").replace("https://", "")}.png'
        date = str(datetime.utcnow())
        try:
            # change default timeout from 30 to 35 seconds
            page.setDefaultNavigationTimeout(35000)
            await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                    'Chrome/83.0.4103.106 Safari/537.36')
            await page.goto(url)
            await page.screenshot({'path': path})
        except Exception as e:
            print(f'An exception has occurred attempting to screenshot: {url} : {e}')
            path = ""
        finally:
            # Clean up everything whether screenshot is taken or not
            await asyncio.sleep(2)
            await page.close()
            await context.close()
            await browser.close()
            return date, url, path
