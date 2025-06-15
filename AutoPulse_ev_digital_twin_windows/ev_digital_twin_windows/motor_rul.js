// Function to calculate motor Remaining Useful Life (RUL)
function updateMotorRUL() {
    // Get references to the UI elements
    const motorRulElement = document.getElementById('motorRul');
    const motorRulBar = document.getElementById('motorRulBar');
    const motorFailureTimeElement = document.getElementById('motorFailureTime');
    
    // Calculate temperature stress factor
    // Higher temperatures reduce motor life exponentially
    const tempDelta = Math.max(0, vehicleState.motorTemperature - motorParams.nominalTemperature);
    // Make temperature effect much less severe
    const tempStressFactor = Math.pow(motorParams.temperatureCoefficient, tempDelta / 30);
    
    // Calculate load stress factor
    // Higher loads (torque) reduce motor life, but make the effect much more gradual
    const nominalTorque = vehicleParams.motorPower * 1000 / (vehicleParams.motorNominalSpeed * 2 * Math.PI / 60);
    const torqueRatio = Math.abs(vehicleState.motorTorque) / nominalTorque;
    // Reduce the impact of speed on RUL by using a much smaller coefficient
    const loadStressFactor = torqueRatio > motorParams.nominalLoad ? 
        1 - (torqueRatio - motorParams.nominalLoad) * (motorParams.wearCoefficient * 0.05) : 
        1;
    
    // Calculate combined stress factor with a minimum to prevent too rapid degradation
    const combinedStressFactor = Math.max(0.95, tempStressFactor * loadStressFactor);
    
    // Calculate remaining hours based on nominal life and stress factors
    // Use a more stable approach that doesn't fluctuate as much with speed changes
    const remainingHours = motorParams.nominalLife * combinedStressFactor;
    
    // Calculate days until failure based on current usage pattern
    // Assuming 8 hours of operation per day
    const daysUntilFailure = Math.round(remainingHours / 8);
    
    // Update UI elements
    motorRulElement.textContent = Math.round(remainingHours);
    motorFailureTimeElement.textContent = daysUntilFailure;
    
    // Update health bar
    const healthPercentage = Math.min(100, (remainingHours / motorParams.nominalLife) * 100);
    motorRulBar.style.width = `${healthPercentage}%`;
    
    // Update color based on health
    if (healthPercentage > 80) {
        motorRulBar.className = 'health-bar bg-success';
    } else if (healthPercentage > 50) {
        motorRulBar.className = 'health-bar bg-info';
    } else if (healthPercentage > 20) {
        motorRulBar.className = 'health-bar bg-warning';
    } else {
        motorRulBar.className = 'health-bar bg-danger';
    }
}

// Variables for range calculation timing
let lastRangeUpdateTime = 0;
const RANGE_UPDATE_INTERVAL = 60; // Update range every 60 seconds

// Function to calculate remaining distance based on battery state and current consumption
function updateRemainingDistance() {
    // Get reference to the UI element
    const dashRemainingDistance = document.getElementById('dashRemainingDistance');
    
    // Only update range calculation once per minute
    if (currentTime - lastRangeUpdateTime < RANGE_UPDATE_INTERVAL && lastRangeUpdateTime > 0) {
        return; // Skip update if not enough time has passed
    }
    
    // Update the last range update time
    lastRangeUpdateTime = currentTime;
    
    // Calculate average consumption at current speed (kWh/km)
    // Use a more realistic consumption model
    let avgConsumption;
    if (vehicleState.speed < 1) {
        // Vehicle is nearly stopped
        avgConsumption = 0.15; // Default consumption at low speeds
    } else {
        // Use a more realistic consumption model based on speed
        // Typical EV consumption ranges from 0.15-0.25 kWh/km depending on speed
        const speedKmh = vehicleState.speed * 3.6;
        if (speedKmh < 50) {
            avgConsumption = 0.15 + (speedKmh / 500); // Lower consumption at lower speeds
        } else if (speedKmh < 100) {
            avgConsumption = 0.17 + (speedKmh - 50) / 400; // Medium consumption at medium speeds
        } else {
            avgConsumption = 0.20 + (speedKmh - 100) / 500; // Higher consumption at higher speeds
        }
    }
    
    // Calculate remaining energy in the battery (kWh)
    const remainingEnergy = vehicleState.batterySoc * vehicleParams.batteryCapacity;
    
    // Calculate remaining distance (km) with a more realistic model
    const remainingDistance = avgConsumption > 0 ? 
        remainingEnergy / avgConsumption : 
        0;
    
    // Update UI element with a more reasonable range value
    dashRemainingDistance.textContent = Math.round(remainingDistance);
}

// Function to update dashboard with all values
function updateDashboard() {
    // Update standard dashboard values
    dashSpeed.textContent = (vehicleState.speed * 3.6).toFixed(1);
    dashPower.textContent = vehicleState.powerDemand.toFixed(1);
    dashBattery.textContent = (vehicleState.batterySoc * 100).toFixed(1);
    
    // Fix distance calculation to be more accurate
    // Distance should be speed * time, not an arbitrary value
    dashDistance.textContent = vehicleState.distance.toFixed(1);
    
    dashMotorSpeed.textContent = Math.round(vehicleState.motorSpeed);
    dashTorque.textContent = vehicleState.motorTorque.toFixed(1);
    dashBatteryTemp.textContent = vehicleState.batteryTemperature.toFixed(1);
    dashMotorTemp.textContent = vehicleState.motorTemperature.toFixed(1);
    
    // Update motor efficiency display
    const motorEfficiencyElement = document.getElementById('motorEfficiency');
    if (motorEfficiencyElement) {
        motorEfficiencyElement.textContent = vehicleState.motorEfficiency.toFixed(1) + '%';
        
        // Update efficiency bar
        const motorEfficiencyBar = document.getElementById('motorEfficiencyBar');
        if (motorEfficiencyBar) {
            motorEfficiencyBar.style.width = vehicleState.motorEfficiency + '%';
        }
    }
    
    // Update motor temperature display in the Motor Performance section
    const motorTempValueElement = document.getElementById('motorTempValue');
    if (motorTempValueElement) {
        motorTempValueElement.textContent = vehicleState.motorTemperature.toFixed(1) + '°C';
        
        // Update temperature bar
        const motorTempBar = document.getElementById('motorTempBar');
        if (motorTempBar) {
            // Calculate percentage (assuming max temp of 150°C)
            const tempPercentage = Math.min(100, (vehicleState.motorTemperature / 150) * 100);
            motorTempBar.style.width = tempPercentage + '%';
            
            // Update color based on temperature
            if (vehicleState.motorTemperature < 60) {
                motorTempBar.className = 'health-bar bg-success';
            } else if (vehicleState.motorTemperature < 90) {
                motorTempBar.className = 'health-bar bg-warning';
            } else {
                motorTempBar.className = 'health-bar bg-danger';
            }
        }
    }
    
    // Update remaining distance (only updates every minute now)
    updateRemainingDistance();
    
    // Update motor RUL and failure prediction
    updateMotorRUL();
    
    // Update motor visualization
    motorCurrentSpeed.textContent = Math.round(vehicleState.motorSpeed);
    motorCurrentTorque.textContent = vehicleState.motorTorque.toFixed(1);
    motorCurrentTemp.textContent = vehicleState.motorTemperature.toFixed(1);
}
