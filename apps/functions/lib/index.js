"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.scrapeJRAData = exports.helloWorld = void 0;
const https_1 = require("firebase-functions/v2/https");
const firebase_functions_1 = require("firebase-functions");
const app_1 = require("firebase-admin/app");
const firestore_1 = require("firebase-admin/firestore");
const jraScraper_1 = require("./scraper/jraScraper");
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
    try {
        // スクレイピング実行
        const races = await (0, jraScraper_1.scrapeJRAData)();
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
});
/**
 * Firestoreにレースデータを保存
 */
async function saveRacesToFirestore(races) {
    if (races.length === 0)
        return 0;
    const batch = db.batch();
    let savedCount = 0;
    for (const race of races) {
        try {
            const docRef = db.collection('races').doc();
            batch.set(docRef, Object.assign(Object.assign({}, race), { date: firestore_1.Timestamp.fromDate(race.date), scrapedAt: firestore_1.Timestamp.fromDate(race.scrapedAt) }));
            savedCount++;
        }
        catch (error) {
            firebase_functions_1.logger.error('Error saving race to Firestore', { race, error });
        }
    }
    try {
        await batch.commit();
        firebase_functions_1.logger.info('Batch committed successfully', { savedCount });
    }
    catch (error) {
        firebase_functions_1.logger.error('Error committing batch', { error });
        throw error;
    }
    return savedCount;
}
//# sourceMappingURL=index.js.map