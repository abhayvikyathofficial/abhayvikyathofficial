// node render_svg.cjs in.svg out.png 480
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

(async () => {
  const [input, output, sizeArg] = process.argv.slice(2);
  const size = Number(sizeArg || 480);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: size, height: size } });
  const svg = fs.readFileSync(path.resolve(input), "utf8");
  await page.setContent(
    `<html><body style="margin:0;background:transparent">
       <div id="box" style="width:${size}px;height:${size}px;display:flex;align-items:center;justify-content:center">${svg}</div>
     </body></html>`,
  );
  await page.evaluate((size) => {
    const el = document.querySelector("#box svg");
    el.removeAttribute("width");
    el.removeAttribute("height");
    el.style.width = size + "px";
    el.style.height = size + "px";
  }, size);
  await page.screenshot({ path: output, omitBackground: true });
  await browser.close();
})();
