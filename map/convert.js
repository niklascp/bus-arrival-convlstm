const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.setViewport({width: 800, height: 1000});
  await page.goto('file://C:/Users/ncp/Jupyter/bus-arrival-convlstm/map/map.html');
  await page.screenshot({path: 'map.png'});

  await browser.close();
})();