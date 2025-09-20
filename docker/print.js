const fs = require('fs');
const path = require('path');
const argv = require('minimist')(process.argv.slice(2));

(async () => {
    try {
        const puppeteer = (await import('puppeteer')).default || (await import('puppeteer'));
        const input = argv._[0] || '/work/input.html';
        const output = argv._[1] || '/work/output.pdf';
        const waitFor = argv.waitFor || 'networkidle0';
        const paperFormat = argv.format || 'A4';
        const margin = argv.margin || '10mm';
        const scale = Number(argv.scale || 1.0);

        const browser = await puppeteer.launch({
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
            defaultViewport: { width: 1200, height: 800 }
        });

        const page = await browser.newPage();

        let url;
        if (fs.existsSync(input)) {
            url = 'file://' + path.resolve(input);
        } else {
            url = input;
        }

        await page.goto(url, { waitUntil: waitFor, timeout: 180000 });

        try { await page.evaluate(() => document.fonts && document.fonts.ready); } catch { }

        await page.evaluate(() => {
            return new Promise((resolve) => {
                try {
                    if (window.MathJax && MathJax.typesetPromise) {
                        MathJax.typesetPromise().then(() => resolve(true)).catch(() => resolve(true));
                    } else if (window.katex) {
                        const done = () => resolve(true);
                        if (document.readyState === 'complete') done();
                        else window.addEventListener('load', done, { once: true });
                    } else {
                        resolve(true);
                    }
                } catch (e) {
                    resolve(true);
                }
            });
        });

        await page.pdf({
            path: output,
            format: paperFormat,
            margin: { top: margin, bottom: margin, left: margin, right: margin },
            printBackground: true,
            scale
        });

        await browser.close();
        console.log('html → pdf: wrote', output);
    } catch (err) {
        console.error('Error in print.js:', err);
        process.exit(1);
    }
})();
