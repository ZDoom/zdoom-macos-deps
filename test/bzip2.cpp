#include <string.h>
#include <bzlib.h>

int main()
{
    constexpr size_t BUFFER_SIZE = 1024;
    char reference[BUFFER_SIZE];

    for (size_t i = 0; i < BUFFER_SIZE; ++i)
    {
        reference[i] = static_cast<unsigned char>(i % 47);
    }

    bz_stream stream = {};
    AEDI_EXPECT(BZ2_bzCompressInit(&stream, 1, 0, 0) == BZ_OK);

    char compressed[BUFFER_SIZE] = {};

    stream.next_in = reference;
    stream.avail_in = BUFFER_SIZE;
    stream.next_out = compressed;
    stream.avail_out = BUFFER_SIZE;

    AEDI_EXPECT(BZ2_bzCompress(&stream, BZ_FINISH) == BZ_STREAM_END);
    AEDI_EXPECT(BZ2_bzCompressEnd(&stream) == BZ_OK);

    stream = {};

    AEDI_EXPECT(BZ2_bzDecompressInit(&stream, 0, 0) == BZ_OK);

    char decompressed[BUFFER_SIZE] = {};

    stream.next_in = compressed;
    stream.avail_in = BUFFER_SIZE;
    stream.next_out = decompressed;
    stream.avail_out = BUFFER_SIZE;

    AEDI_EXPECT(BZ2_bzDecompress(&stream) == BZ_STREAM_END);
    AEDI_EXPECT(BZ2_bzDecompressEnd(&stream) == BZ_OK);

    AEDI_EXPECT(memcmp(reference, decompressed, BUFFER_SIZE) == 0);

    return 0;
}
