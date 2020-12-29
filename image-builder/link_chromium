import os

from pyppeteer import chromium_downloader

folder = f'/home/flexget/.local/share/pyppeteer/local-chromium/{chromium_downloader.REVISION}/chrome-linux'
chrome_file = f'{folder}/chrome'
if not os.path.isfile(chrome_file):
    os.makedirs(folder, exist_ok=True)
    os.symlink('/usr/bin/chromium-browser', chrome_file)
