// JRAサイトのHTMLをモック
export const mockJraCalendarHtml = `
<!DOCTYPE html>
<html>
<head>
    <title>開催日程 2024年10月 JRA</title>
</head>
<body>
    <div class="calendar">
        <a href="/keiba/calendar2025/2025/10/1004.html">4</a>
        <a href="/keiba/calendar2025/2025/10/1005.html">5</a>
    </div>
</body>
</html>
`

export const mockJraRaceDayHtml = `
<!DOCTYPE html>
<html>
<head>
    <title>レース詳細</title>
</head>
<body>
    <div class="race-info">
        <div class="race">
            <span class="race-number">1レース</span>
            <span class="race-name">テストレース1</span>
            <span class="start-time">10:05</span>
        </div>
        <div class="race">
            <span class="race-number">2レース</span>
            <span class="race-name">テストレース2</span>
            <span class="start-time">10:35</span>
        </div>
    </div>
</body>
</html>
`
