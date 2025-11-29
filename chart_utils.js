// Utility functions for charts and data visualization
class ChartUtils {
    static createMembershipGrowthChart(data, canvasId) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const labels = data.map(item => item.month);
        const members = data.map(item => item.count);
        
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'New Members',
                    data: members,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Membership Growth Over Time'
                    }
                }
            }
        });
    }
    
    static createAttendanceChart(data, canvasId) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const labels = data.map(item => item.event);
        const attendance = data.map(item => item.count);
        
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Attendance',
                    data: attendance,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Event Attendance'
                    }
                }
            }
        });
    }
}