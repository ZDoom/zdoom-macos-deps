#include <FLAC/all.h>

int main()
{
    FLAC__StreamDecoder* decoder = FLAC__stream_decoder_new();
    AEDI_EXPECT(decoder != nullptr);
    AEDI_EXPECT(FLAC__stream_decoder_set_md5_checking(decoder, true));
    FLAC__stream_decoder_delete(decoder);

    return 0;
}
