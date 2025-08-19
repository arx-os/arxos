const puppeteer = require('puppeteer');

async function captureCurrentView() {
    const browser = await puppeteer.launch({
        headless: true,
        defaultViewport: {
            width: 1920,
            height: 1080
        }
    });

    try {
        console.log('Capturing current Arxos test view...');
        const page = await browser.newPage();
        
        // Go to the test page
        await page.goto('http://localhost:8080/arxos_test.html', {
            waitUntil: 'networkidle2',
            timeout: 10000
        });
        
        // Wait for canvas to load
        await page.waitForSelector('#canvas', { timeout: 5000 });
        
        // Wait for initial data load
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Click Load All Objects button
        await page.evaluate(() => {
            loadAllObjects();
        });
        
        // Wait for objects to load
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Take screenshot
        await page.screenshot({ 
            path: 'arxos_current_view.png',
            fullPage: false 
        });
        console.log('✓ Saved arxos_current_view.png');
        
        // Get statistics
        const stats = await page.evaluate(() => {
            return {
                totalObjects: document.getElementById('total-objects')?.textContent,
                visibleObjects: document.getElementById('visible-objects')?.textContent,
                highConf: document.getElementById('high-conf')?.textContent,
                medConf: document.getElementById('med-conf')?.textContent,
                lowConf: document.getElementById('low-conf')?.textContent,
                zoom: document.getElementById('zoom-level')?.textContent
            };
        });
        
        console.log('\n=== Current Stats ===');
        console.log('Total Objects:', stats.totalObjects);
        console.log('Visible Objects:', stats.visibleObjects);
        console.log('Zoom Level:', stats.zoom);
        
        // Get a sample of objects
        const objects = await page.evaluate(() => {
            if (window.state && window.state.arxObjects) {
                return window.state.arxObjects.slice(0, 5).map(obj => ({
                    type: obj.type,
                    system: obj.system,
                    x: Math.round(obj.x),
                    y: Math.round(obj.y),
                    width: obj.width,
                    height: obj.height
                }));
            }
            return [];
        });
        
        console.log('\n=== Sample Objects ===');
        console.log(JSON.stringify(objects, null, 2));
        
    } catch (error) {
        console.error('Error capturing view:', error);
    } finally {
        await browser.close();
    }
}

captureCurrentView().then(() => {
    console.log('\n✅ Screenshot captured!');
    process.exit(0);
}).catch(error => {
    console.error(error);
    process.exit(1);
});