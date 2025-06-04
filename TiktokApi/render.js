import { JSDOM, VirtualConsole } from 'jsdom'; // Layer jsdomから
import { gotScraping } from 'got-scraping'; // Layer got-scrapingから

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function getApiUrlWithVerificationToken(body, url) {
  // JSDOMを使用してAPIセッションヘッダーを取得
  console.log('JSDOMでAPIセッションヘッダーを取得開始...');
  console.log('ページURL: ', url);
  console.log('ページ内容の長さ: ', body.length);

  const virtualConsole = new VirtualConsole();
  const { window } = new JSDOM(body, {
    url,
    contentType: 'text/html',
    runScripts: 'dangerously',
    resources: 'usable',
    pretendToBeVisual: false,
    virtualConsole,
  });

  virtualConsole.on('error', (err) => {
    // JSDOMエラーをログ
    console.error('JSDOMエラー: ', err);
  });

  const apiHeaderKeys = ['anonymous-user-id', 'timestamp', 'user-sign'];
  const apiValues = {};
  let retries = 10;
  let headersFound = false;

  window.XMLHttpRequest.prototype.setRequestHeader = (name, value) => {
    if (apiHeaderKeys.includes(name)) {
      apiValues[name] = value;
      console.log(`取得したヘッダー: ${name}=${value}`);
      if (Object.keys(apiValues).length === apiHeaderKeys.length) {
        headersFound = true;
        console.log('すべてのヘッダーを取得: ', apiValues);
      }
    }
  };

  window.XMLHttpRequest.prototype.open = (method, urlToOpen) => {
    console.log(`XHRリクエスト開始: ${method} ${urlToOpen}`);
  };

  // ヘッダー取得ロジック
  console.log('ヘッダー取得ループ開始...');
  while (retries > 0 && !headersFound) {
    console.log(`試行残り: ${retries}, 取得済みヘッダー: `, Object.keys(apiValues));
    await sleep(1000);
    retries--;
  }

  console.log('ヘッダー取得ループ終了、headersFound: ', headersFound);
  window.close();

  if (!headersFound) {
    console.error('最終的に取得できたヘッダー: ', apiValues);
    throw new Error('トークン生成に失敗: 必要なヘッダーをすべて抽出できませんでした。');
  }

  console.log('API認証ヘッダーの取得に成功: ', apiValues);
  return apiValues;
}

export async function getHeaders() {
  // 初期ページをフェッチしてヘッダーを生成
  console.log('ヘッダー生成のために初期ページをフェッチ中...');
  const url = 'https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pad/en';
  try {
    console.log('gotScrapingリクエスト開始: ', url);
    const response = await gotScraping({
      url,
      timeout: { request: 30000 },
    });
    console.log('ページフェッチ成功、ステータスコード: ', response.statusCode);
    return await getApiUrlWithVerificationToken(response.body.toString(), url);
  } catch (error) {
    console.error(`${url} からページフェッチ失敗: `, error.message);
    throw error;
  }
}