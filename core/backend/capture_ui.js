const puppeteer = require('puppeteer');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function captureScreenshots() {
    const browser = await puppeteer.launch({
        headless: true,
        defaultViewport: {
            width: 1920,
            height: 1080
        }
    });

    try {
        // Capture ArxOS Viewer
        console.log('Capturing ArxOS Viewer...');
        const viewerPage = await browser.newPage();
        await viewerPage.goto('http://localhost:8080/arxos_viewer.html', {
            waitUntil: 'networkidle2',
            timeout: 10000
        });
        
        // Wait for canvas to render
        await viewerPage.waitForSelector('#canvas', { timeout: 5000 });
        await sleep(2000); // Give it time to load
        
        // Click "Load All Objects" button
        await viewerPage.evaluate(() => {
            if (typeof loadAllObjects === 'function') {
                loadAllObjects();
            }
        });
        await sleep(3000); // Wait for objects to load
        
        await viewerPage.screenshot({ 
            path: 'arxos_viewer_screenshot.png',
            fullPage: false 
        });
        console.log('✓ Saved arxos_viewer_screenshot.png');

        // Get some stats from the viewer
        const stats = await viewerPage.evaluate(() => {
            return {
                totalObjects: document.getElementById('total-objects')?.textContent,
                visibleObjects: document.getElementById('visible-objects')?.textContent,
                highConf: document.getElementById('high-conf')?.textContent,
                medConf: document.getElementById('med-conf')?.textContent,
                lowConf: document.getElementById('low-conf')?.textContent,
            };
        });
        
        console.log('\n=== ArxOS Viewer Stats ===');
        console.log('Total Objects:', stats.totalObjects);
        console.log('Visible Objects:', stats.visibleObjects);
        console.log('High Confidence:', stats.highConf);
        console.log('Medium Confidence:', stats.medConf);
        console.log('Low Confidence:', stats.lowConf);

        // Capture PDF Upload interface
        console.log('\nCapturing PDF Upload interface...');
        const uploadPage = await browser.newPage();
        await uploadPage.goto('http://localhost:8080/pdf_upload.html', {
            waitUntil: 'networkidle2',
            timeout: 10000
        });
        
        await sleep(2000);
        await uploadPage.screenshot({ 
            path: 'pdf_upload_screenshot.png',
            fullPage: false 
        });
        console.log('✓ Saved pdf_upload_screenshot.png');

        // Capture Working BIM viewer
        console.log('\nCapturing Working BIM viewer...');
        const bimPage = await browser.newPage();
        await bimPage.goto('http://localhost:8080/working_bim.html', {
            waitUntil: 'networkidle2',
            timeout: 10000
        });
        
        await sleep(2000);
        
        // Try to load objects in BIM viewer
        await bimPage.evaluate(() => {
            if (typeof loadAllObjects === 'function') {
                loadAllObjects();
            }
        });
        await sleep(2000);
        
        await bimPage.screenshot({ 
            path: 'working_bim_screenshot.png',
            fullPage: false 
        });
        console.log('✓ Saved working_bim_screenshot.png');

        // Try different view modes
        console.log('\nCapturing different view modes...');
        
        // System view
        await viewerPage.evaluate(() => {
            if (typeof setViewMode === 'function') {
                setViewMode('system');
            }
        });
        await sleep(1000);
        await viewerPage.screenshot({ 
            path: 'arxos_viewer_system_view.png',
            fullPage: false 
        });
        console.log('✓ Saved arxos_viewer_system_view.png');
        
        // Type view
        await viewerPage.evaluate(() => {
            if (typeof setViewMode === 'function') {
                setViewMode('type');
            }
        });
        await sleep(1000);
        await viewerPage.screenshot({ 
            path: 'arxos_viewer_type_view.png',
            fullPage: false 
        });
        console.log('✓ Saved arxos_viewer_type_view.png');

        // Zoom to room level
        await viewerPage.evaluate(() => {
            if (typeof setZoom === 'function') {
                setZoom(6);
            }
        });
        await sleep(1000);
        await viewerPage.screenshot({ 
            path: 'arxos_viewer_room_zoom.png',
            fullPage: false 
        });
        console.log('✓ Saved arxos_viewer_room_zoom.png');

    } catch (error) {
        console.error('Error capturing screenshots:', error);
    } finally {
        await browser.close();
    }
}

// Run the capture
captureScreenshots().then(() => {
    console.log('\n✅ All screenshots captured successfully!');
    console.log('View them with:');
    console.log('  open arxos_viewer_screenshot.png');
    console.log('  open pdf_upload_screenshot.png');
    console.log('  open working_bim_screenshot.png');
    process.exit(0);
}).catch(error => {
    console.error(error);
    process.exit(1);
});