#include <mad.h>

int main()
{
    AEDI_EXPECT(mad_version[0] != '\0');
    AEDI_EXPECT(mad_build[0] != '\0');

    mad_stream stream = {};
    mad_stream_init(&stream);
    AEDI_EXPECT(stream.error == MAD_ERROR_NONE);
    mad_stream_finish(&stream);

    return 0;
}
