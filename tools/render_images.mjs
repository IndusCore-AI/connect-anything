// Render docs/img/src/*.html to docs/img/*.png at 2x. Needs Playwright:
//   PLAYWRIGHT=/path/to/node_modules/playwright node tools/render_images.mjs
import { createRequire } from 'node:module';
import { readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');
const root = join(dirname(fileURLToPath(import.meta.url)), '..', 'docs', 'img');
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1360, height: 800 }, deviceScaleFactor: 2 });
for (const f of readdirSync(join(root, 'src')).filter((f) => f.endsWith('.html'))) {
  await page.goto('file://' + join(root, 'src', f));
  const card = await page.$('main');
  await card.screenshot({ path: join(root, f.replace('.html', '.png')) });
  console.log('rendered', f);
}
await browser.close();
