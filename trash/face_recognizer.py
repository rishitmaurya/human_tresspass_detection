with open(LOG_FILE, "w", encoding='utf-8') as f:
    f.write("""
    <html>
    <head>
        <style>
            /* ... your existing styles ... */
        </style>
        <script>
        let allRows = [];
        let allDates = new Set();

        window.onload = function() {
            // Collect all rows and dates
            allRows = Array.from(document.querySelectorAll("tbody tr[data-date]"));
            allRows.forEach(row => allDates.add(row.getAttribute("data-date")));
            populateDateDropdown();
            filterLogs();
        };

        function populateDateDropdown() {
            const dateSelect = document.getElementById("dateSelect");
            dateSelect.innerHTML = '<option value="all">All Dates</option>';
            Array.from(allDates).sort().forEach(date => {
                dateSelect.innerHTML += `<option value="${date}">${date}</option>`;
            });
        }

        function filterLogs() {
            const date = document.getElementById("dateSelect").value;
            const search = document.getElementById("searchInput").value.toLowerCase();
            allRows.forEach(row => {
                const rowDate = row.getAttribute("data-date");
                const rowText = row.innerText.toLowerCase();
                let show = (date === "all" || rowDate === date);
                if (search) {
                    show = show && rowText.includes(search);
                }
                row.style.display = show ? "" : "none";
            });
        }
        </script>
    </head>
    <body>
        <div class="header">
            <h2>Intrusion Detection Log</h2>
            <span class="total-count">Total Detections: 0</span>
            <label for="dateSelect" style="margin-left:2rem;">View by Date:</label>
            <select id="dateSelect" onchange="filterLogs()" style="margin-right:2rem;"></select>
            <input id="searchInput" type="text" placeholder="Search by date, time, name..." onkeyup="filterLogs()" style="padding:0.5rem; border-radius:4px; border:1px solid #ccc;">
            <button class="download-btn" onclick="downloadData()">Download</button>
        </div>
        <script>
        function showAlert() {
            const alert = document.getElementById('successAlert');
            alert.style.display = 'block';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 3000);
        }
        function downloadData() {
            window.location.href = 'download://trigger';
            return false;
        }
        </script>
        <table>
            <thead>
            <tr>
                <th>S.No</th>
                <th>Date</th>
                <th>Time</th>
                <th>Event</th>
                <th>Name</th>
                <th>Evidence</th>
            </tr>
            </thead>
            <tbody>
    """)