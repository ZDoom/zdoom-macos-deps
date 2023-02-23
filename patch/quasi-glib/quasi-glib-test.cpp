
#include <assert.h>
#include <glib.h>

constexpr int REC_MUTEX_LOCK_COUNT = 4;

struct ThreadData
{
    GCond* cond;
    GMutex* mutex;
    GRecMutex* recMutex;
    GPrivate* tls;
    bool flag;
};

static void* ThreadFunc(void* arg)
{
    ThreadData* threadData = reinterpret_cast<ThreadData*>(arg);
    GPrivate* tls = threadData->tls;

    {
        assert(g_private_get(tls) == nullptr);

        const gpointer TLS_REF_VALUE = gpointer(0xFEDCBA0987654321);
        g_private_set(tls, TLS_REF_VALUE);

        assert(g_private_get(tls) == TLS_REF_VALUE);
    }

    GMutex* mutex = threadData->mutex;
    g_mutex_lock(mutex);
    threadData->flag = true;
    g_cond_signal(threadData->cond);
    g_mutex_unlock(mutex);

    GRecMutex* recMutex = threadData->recMutex;
    g_rec_mutex_lock(recMutex);
    g_rec_mutex_unlock(recMutex);

    return nullptr;
}

int main()
{
    g_clear_error(nullptr);
    g_return_if_fail_warning("", "", "");
    assert(g_file_test(nullptr, GFileTest(0)) == 0);
    assert(g_get_monotonic_time() > 0);

    GRecMutex recMutex;
    g_rec_mutex_init(&recMutex);

    for (int i = 0; i < REC_MUTEX_LOCK_COUNT; ++i)
        g_rec_mutex_lock(&recMutex);

    GCond cond;
    g_cond_init(&cond);

    GMutex mutex;
    g_mutex_init(&mutex);

    GPrivate tls = G_PRIVATE_INIT(nullptr);
    {
        assert(g_private_get(&tls) == nullptr);

        const gpointer TLS_REF_VALUE = gpointer(0x1234567890ABCDEF);
        g_private_set(&tls, TLS_REF_VALUE);

        assert(g_private_get(&tls) == TLS_REF_VALUE);
    }

    ThreadData threadData = { &cond, &mutex, &recMutex, &tls, false };

    GThread* thread = g_thread_try_new("", ThreadFunc, &threadData, nullptr);
    assert(thread);

    g_usleep(10'000);

    g_mutex_lock(&mutex);
    while (!threadData.flag)
        g_cond_wait(&cond, &mutex);
    g_mutex_unlock(&mutex);

    g_cond_broadcast(&cond);
    g_cond_clear(&cond);

    for (int i = 0; i < REC_MUTEX_LOCK_COUNT; ++i)
        g_rec_mutex_unlock(&recMutex);

    g_thread_join(thread);
    g_thread_unref(thread);

    g_mutex_clear(&mutex);
    g_rec_mutex_clear(&recMutex);
}
