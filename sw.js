const CACHE_NAME = 'ict-quiz-v1';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    // 如果 quiz.js 不存在，先注释掉
    // '/static/js/quiz.js',
];

// 安装时缓存
self.addEventListener('install', event => {
    console.log('🔧 Service Worker 正在安装...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('📦 开始缓存文件...');
                // 逐个缓存，避免一个失败全失败
                return Promise.all(
                    urlsToCache.map(url => {
                        return cache.add(url).catch(err => {
                            console.warn(`⚠️ 缓存失败: ${url}`, err);
                        });
                    })
                );
            })
            .then(() => {
                console.log('✅ 缓存完成');
                return self.skipWaiting();
            })
    );
});

// 拦截请求
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
            .catch(() => {
                // 离线时的兜底
                return caches.match('/');
            })
    );
});

// 更新时清理旧缓存
self.addEventListener('activate', event => {
    console.log('🚀 Service Worker 激活');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(name => {
                    if (name !== CACHE_NAME) {
                        console.log(`🗑️ 删除旧缓存: ${name}`);
                        return caches.delete(name);
                    }
                })
            );
        }).then(() => {
            return self.clients.claim();
        })
    );
});