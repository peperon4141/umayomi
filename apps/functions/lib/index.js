"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.scrapeJRAData = exports.helloWorld = void 0;
const https_1 = require("firebase-functions/v2/https");
const firebase_functions_1 = require("firebase-functions");
const playwright_1 = require("playwright");
const app_1 = require("firebase-admin/app");
const firestore_1 = require("firebase-admin/firestore");
// Firebase Admin SDKを初期化
(0, app_1.initializeApp)();
const db = (0, firestore_1.getFirestore)();
/**
 * HelloWorld Cloud Function
 * TDDで作成されたシンプルな関数
 */
exports.helloWorld = (0, https_1.onRequest)((request, response) => {
    firebase_functions_1.logger.info('HelloWorld function called', {
        method: request.method,
        url: request.url
    });
    response.send('Hello World!');
});
/**
 * JRAスクレイピング Cloud Function
 * Playwrightを使用してJRAのレース結果を取得
 */
exports.scrapeJRAData = (0, https_1.onRequest)({ timeoutSeconds: 300, memory: '1GiB' }, async (request, response) => {
    firebase_functions_1.logger.info('JRA scraping function called', {
        method: request.method,
        url: request.url
    });
    let browser = null;
    try {
        // Playwrightブラウザを起動
        browser = await playwright_1.chromium.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        const context = await browser.newContext({
            userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        });
        const page = await context.newPage();
        // JRAのレース結果ページにアクセス（2024年8月のデータを使用）
        const url = 'https://www.jra.go.jp/keiba/result/202408/';
        firebase_functions_1.logger.info('Accessing JRA website', { url });
        // アクセスしたURLの履歴をログに記録
        firebase_functions_1.logger.info('JRA scraping URL history', {
            accessedUrl: url,
            timestamp: new Date().toISOString(),
            userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        });
        await page.goto(url, { waitUntil: 'networkidle' });
        // レース結果のリンクを取得
        const raceLinks = await page.$$eval('a[href*="/result/"]', links => links.map(link => {
            var _a;
            return ({
                href: link.getAttribute('href'),
                text: ((_a = link.textContent) === null || _a === void 0 ? void 0 : _a.trim()) || ''
            });
        }).filter(link => link.href && link.text));
        firebase_functions_1.logger.info('Found race links', { count: raceLinks.length });
        const races = [];
        // 各レース結果ページを処理
        for (const link of raceLinks) {
            try {
                const raceData = await scrapeRaceDetail(page, link.href);
                if (raceData) {
                    races.push(raceData);
                    firebase_functions_1.logger.info('Scraped race data', { raceName: raceData.raceName });
                }
            }
            catch (error) {
                firebase_functions_1.logger.error('Error scraping race', {
                    raceLink: link.text,
                    error: error instanceof Error ? error.message : 'Unknown error'
                });
            }
        }
        firebase_functions_1.logger.info('JRA scraping completed', { racesCount: races.length });
        // Firestoreに保存
        const savedCount = await saveRacesToFirestore(races);
        firebase_functions_1.logger.info('Races saved to Firestore', { savedCount });
        response.send({
            success: true,
            message: 'JRAデータのスクレイピングが完了しました',
            racesCount: races.length,
            savedCount: savedCount,
            races: races
        });
    }
    catch (error) {
        firebase_functions_1.logger.error('JRA scraping failed', {
            error: error instanceof Error ? error.message : 'Unknown error'
        });
        response.status(500).send({
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
        });
    }
    finally {
        if (browser) {
            await browser.close();
        }
    }
});
/**
 * 個別レースの詳細データを取得
 */
async function scrapeRaceDetail(page, raceUrl) {
    try {
        // 相対URLを絶対URLに変換
        const fullUrl = raceUrl.startsWith('http') ? raceUrl : `https://www.jra.go.jp${raceUrl}`;
        await page.goto(fullUrl, { waitUntil: 'networkidle' });
        // レース情報を取得
        const raceInfo = await page.evaluate(() => {
            var _a, _b, _c, _d, _e, _f, _g, _h, _j;
            // 日付を取得
            const dateElement = document.querySelector('.race-date');
            const dateText = ((_a = dateElement === null || dateElement === void 0 ? void 0 : dateElement.textContent) === null || _a === void 0 ? void 0 : _a.trim()) || '';
            // 競馬場を取得
            const racecourseElement = document.querySelector('.racecourse-name');
            const racecourse = ((_b = racecourseElement === null || racecourseElement === void 0 ? void 0 : racecourseElement.textContent) === null || _b === void 0 ? void 0 : _b.trim()) || '';
            // レース名を取得
            const raceNameElement = document.querySelector('.race-name');
            const raceName = ((_c = raceNameElement === null || raceNameElement === void 0 ? void 0 : raceNameElement.textContent) === null || _c === void 0 ? void 0 : _c.trim()) || '';
            // レース番号を取得
            const raceNumberElement = document.querySelector('.race-number');
            const raceNumberText = ((_d = raceNumberElement === null || raceNumberElement === void 0 ? void 0 : raceNumberElement.textContent) === null || _d === void 0 ? void 0 : _d.trim()) || '';
            const raceNumber = parseInt(raceNumberText.replace('R', '')) || 0;
            // グレードを取得
            const gradeElement = document.querySelector('.grade');
            const grade = ((_e = gradeElement === null || gradeElement === void 0 ? void 0 : gradeElement.textContent) === null || _e === void 0 ? void 0 : _e.trim()) || '条件';
            // コース情報を取得
            const courseElement = document.querySelector('.course-info');
            const courseText = ((_f = courseElement === null || courseElement === void 0 ? void 0 : courseElement.textContent) === null || _f === void 0 ? void 0 : _f.trim()) || '';
            const surface = courseText.includes('芝') ? '芝' : courseText.includes('ダート') ? 'ダート' : '障害';
            const distance = parseInt(((_g = courseText.match(/(\d+)m/)) === null || _g === void 0 ? void 0 : _g[1]) || '0') || 0;
            // 天候・馬場状態を取得
            const weatherElement = document.querySelector('.weather');
            const weather = ((_h = weatherElement === null || weatherElement === void 0 ? void 0 : weatherElement.textContent) === null || _h === void 0 ? void 0 : _h.trim()) || '晴';
            const trackElement = document.querySelector('.track-condition');
            const trackCondition = ((_j = trackElement === null || trackElement === void 0 ? void 0 : trackElement.textContent) === null || _j === void 0 ? void 0 : _j.trim()) || '良';
            // レース結果を取得
            const resultRows = document.querySelectorAll('.result-table tbody tr');
            const results = Array.from(resultRows).map((row, index) => {
                var _a, _b, _c, _d, _e, _f;
                const cells = row.querySelectorAll('td');
                if (cells.length < 4)
                    return null;
                return {
                    rank: index + 1,
                    horseName: ((_b = (_a = cells[1]) === null || _a === void 0 ? void 0 : _a.textContent) === null || _b === void 0 ? void 0 : _b.trim()) || '',
                    jockey: ((_d = (_c = cells[2]) === null || _c === void 0 ? void 0 : _c.textContent) === null || _d === void 0 ? void 0 : _d.trim()) || '',
                    odds: parseFloat(((_f = (_e = cells[3]) === null || _e === void 0 ? void 0 : _e.textContent) === null || _f === void 0 ? void 0 : _f.trim()) || '0')
                };
            }).filter(Boolean);
            return {
                date: dateText,
                racecourse,
                raceNumber,
                raceName,
                grade,
                surface,
                distance,
                weather,
                trackCondition,
                results
            };
        });
        if (!raceInfo || !raceInfo.results.length) {
            return null;
        }
        // 日付をパース
        const date = parseDate(raceInfo.date);
        if (!date) {
            firebase_functions_1.logger.warn('Failed to parse date', { date: raceInfo.date });
            return null;
        }
        // Raceオブジェクトを作成
        const race = {
            id: `jra-${date.getTime()}-${raceInfo.raceNumber}`,
            date: date,
            racecourse: raceInfo.racecourse,
            raceNumber: raceInfo.raceNumber,
            raceName: raceInfo.raceName,
            grade: raceInfo.grade,
            surface: raceInfo.surface,
            distance: raceInfo.distance,
            weather: raceInfo.weather,
            trackCondition: raceInfo.trackCondition,
            results: raceInfo.results
        };
        return race;
    }
    catch (error) {
        firebase_functions_1.logger.error('Error scraping race detail', {
            raceUrl,
            error: error instanceof Error ? error.message : 'Unknown error'
        });
        return null;
    }
}
/**
 * 日付文字列をDateオブジェクトに変換
 */
function parseDate(dateStr) {
    try {
        // "2025年10月5日" 形式をパース
        const match = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
        if (match) {
            const year = parseInt(match[1]);
            const month = parseInt(match[2]) - 1; // JavaScriptの月は0ベース
            const day = parseInt(match[3]);
            return new Date(year, month, day);
        }
        // その他の形式も試行
        const date = new Date(dateStr);
        return isNaN(date.getTime()) ? null : date;
    }
    catch (_a) {
        return null;
    }
}
/**
 * レースデータをFirestoreに保存
 */
async function saveRacesToFirestore(races) {
    if (!races.length)
        return 0;
    const batch = db.batch();
    let savedCount = 0;
    for (const race of races) {
        try {
            // 既存データとの重複チェック
            const existingRace = await db.collection('races').doc(race.id).get();
            if (existingRace.exists) {
                firebase_functions_1.logger.info('Race already exists, skipping', { raceId: race.id });
                continue;
            }
            // Firestore用のデータ形式に変換
            const raceData = {
                id: race.id,
                date: firestore_1.Timestamp.fromDate(race.date),
                racecourse: race.racecourse,
                raceNumber: race.raceNumber,
                raceName: race.raceName,
                grade: race.grade,
                surface: race.surface,
                distance: race.distance,
                weather: race.weather,
                trackCondition: race.trackCondition,
                results: race.results,
                createdAt: firestore_1.Timestamp.now(),
                updatedAt: firestore_1.Timestamp.now()
            };
            // バッチに追加
            const raceRef = db.collection('races').doc(race.id);
            batch.set(raceRef, raceData);
            savedCount++;
        }
        catch (error) {
            firebase_functions_1.logger.error('Error preparing race for batch', {
                raceId: race.id,
                error: error instanceof Error ? error.message : 'Unknown error'
            });
        }
    }
    if (savedCount > 0) {
        try {
            await batch.commit();
            firebase_functions_1.logger.info('Batch write completed', { savedCount });
        }
        catch (error) {
            firebase_functions_1.logger.error('Batch write failed', {
                error: error instanceof Error ? error.message : 'Unknown error'
            });
            throw error;
        }
    }
    return savedCount;
}
//# sourceMappingURL=index.js.map