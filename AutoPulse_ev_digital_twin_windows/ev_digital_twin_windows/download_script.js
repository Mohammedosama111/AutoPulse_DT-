// Add event listener for download button
document.getElementById('downloadReportBtn').addEventListener('click', function() {
    const reportType = document.getElementById('reportType').value;
    const reportFormat = document.getElementById('reportFormat').value;
    
    // Create filename based on report type and format
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `ev-simulation-${reportType}-report-${timestamp}.${reportFormat === 'pdf' ? 'pdf' : reportFormat}`;
    
    // Get report content
    let content = '';
    switch (reportType) {
        case 'summary':
            content = generateSummaryReport();
            break;
        case 'battery':
            content = generateBatteryReport();
            break;
        case 'motor':
            content = generateMotorReport();
            break;
        case 'energy':
            content = generateEnergyReport();
            break;
        case 'full':
            content = generateFullReport();
            break;
    }
    
    // Convert content based on format
    let downloadContent = '';
    let mimeType = '';
    
    if (reportFormat === 'html') {
        downloadContent = `<!DOCTYPE html><html><head><title>EV Simulation Report</title>
        <style>body{font-family:Arial,sans-serif;line-height:1.6;margin:20px;} 
        table{border-collapse:collapse;width:100%;margin-bottom:20px;} 
        th,td{border:1px solid #ddd;padding:8px;text-align:left;}
        th{background-color:#f2f2f2;}</style></head><body>${content}</body></html>`;
        mimeType = 'text/html';
    } else if (reportFormat === 'csv') {
        // Simple conversion of HTML tables to CSV
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = content;
        const tables = tempDiv.querySelectorAll('table');
        
        tables.forEach(table => {
            const rows = table.querySelectorAll('tr');
            rows.forEach(row => {
                const cells = row.querySelectorAll('th, td');
                const csvRow = Array.from(cells).map(cell => `"${cell.textContent.trim()}"`).join(',');
                downloadContent += csvRow + '\n';
            });
            downloadContent += '\n';
        });
        mimeType = 'text/csv';
    } else if (reportFormat === 'json') {
        // Create a simple JSON structure with simulation data
        const jsonData = {
            reportType: reportType,
            generatedAt: new Date().toISOString(),
            simulationTime: currentTime,
            vehicle: {
                speed: vehicleState.speed,
                distance: vehicleState.distance,
                power: vehicleState.powerDemand
            },
            battery: {
                soc: vehicleState.batterySoc * 100,
                voltage: vehicleState.batteryVoltage,
                temperature: vehicleState.batteryTemperature
            },
            motor: {
                speed: vehicleState.motorSpeed,
                torque: vehicleState.motorTorque,
                efficiency: vehicleState.motorEfficiency,
                temperature: vehicleState.motorTemperature
            }
        };
        downloadContent = JSON.stringify(jsonData, null, 2);
        mimeType = 'application/json';
    } else if (reportFormat === 'pdf') {
        // For PDF, we'll use a data URI approach with proper PDF MIME type
        // First create the HTML content
        const htmlContent = `<!DOCTYPE html><html><head><title>EV Simulation Report</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
            h1, h2, h3 { color: #333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .header { text-align: center; margin-bottom: 30px; }
            .footer { text-align: center; margin-top: 30px; font-size: 0.8em; color: #666; }
        </style>
        </head><body>
        <div class="header">
            <h1>Electric Vehicle Digital Twin Simulation Report</h1>
            <p>Generated on: ${new Date().toLocaleString()}</p>
        </div>
        ${content}
        <div class="footer">
            <p>© ${new Date().getFullYear()} EV Digital Twin Simulation</p>
        </div>
        </body></html>`;
        
        // Create a simple PDF structure (minimal valid PDF)
        // This is a very basic PDF structure that should be valid and openable
        const pdfContent = `%PDF-1.4
1 0 obj
<</Type /Catalog /Pages 2 0 R>>
endobj
2 0 obj
<</Type /Pages /Kids [3 0 R] /Count 1>>
endobj
3 0 obj
<</Type /Page /Parent 2 0 R /Resources 4 0 R /MediaBox [0 0 612 792] /Contents 6 0 R>>
endobj
4 0 obj
<</Font <</F1 5 0 R>>>>
endobj
5 0 obj
<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>
endobj
6 0 obj
<</Length 90>>
stream
BT
/F1 12 Tf
50 700 Td
(EV Digital Twin Simulation Report) Tj
50 680 Td
(Please view the HTML version for full details.) Tj
ET
endstream
endobj
xref
0 7
0000000000 65535 f
0000000009 00000 n
0000000056 00000 n
0000000111 00000 n
0000000212 00000 n
0000000253 00000 n
0000000321 00000 n
trailer
<</Size 7 /Root 1 0 R>>
startxref
461
%%EOF`;
        
        downloadContent = pdfContent;
        mimeType = 'application/pdf';
    }
    
    // Create download link
    const blob = new Blob([downloadContent], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    // Enable the download button (it might have been disabled before report generation)
    document.getElementById('downloadReportBtn').disabled = false;
});
