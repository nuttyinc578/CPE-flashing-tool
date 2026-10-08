// Headless QA against our own site; no personal browser profile is opened.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('fs');
const {pathToFileURL} = require('url');
const path = require('path');
let activeBrowser;
(async () => {
  const browser = await chromium.launch({headless:true, ...(process.env.PREVIEW_BROWSER ? {executablePath:process.env.PREVIEW_BROWSER} : {})});
  activeBrowser = browser;
  const errors = [];
  const page = await browser.newPage();
  page.on('pageerror', error => errors.push(error.message));
  fs.mkdirSync('build', {recursive:true});
  for (const [name,width,height] of [['desktop',1440,1000],['mobile',390,844]]) {
    await page.setViewportSize({width,height});
    await page.goto(process.env.PREVIEW_URL || pathToFileURL(path.resolve('site/index.html')).href, {waitUntil:'networkidle'});
    const geometry = await page.evaluate(() => ({width:innerWidth, document:document.documentElement.scrollWidth}));
    if (geometry.document > geometry.width) throw Error(name+' has horizontal overflow');
    if (await page.locator('h1').count() !== 1) throw Error('Missing main heading');
    await page.locator('details').first().locator('summary').click();
    if (!(await page.locator('details').first().getAttribute('open') !== null)) throw Error('FAQ did not open');
    await page.screenshot({path:'build/site-'+name+'.png',fullPage:true});
    console.log(name+': layout, FAQ interaction and screenshot verified');
  }
  if (errors.length) throw Error(errors.join('\n'));
  await browser.close();
})().catch(async error => {console.error(error); if(activeBrowser) await activeBrowser.close(); process.exit(1);});
