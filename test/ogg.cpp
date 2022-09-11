#include <ogg/ogg.h>

int main()
{
    ogg_sync_state sync;
    AEDI_EXPECT(ogg_sync_init(&sync) == 0);
    AEDI_EXPECT(ogg_sync_check(&sync) == 0);

    ogg_stream_state stream;
    AEDI_EXPECT(ogg_stream_init(&stream, 1) == 0);
    AEDI_EXPECT(ogg_stream_check(&stream) == 0);

    return 0;
}
