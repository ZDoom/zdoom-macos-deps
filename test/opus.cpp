#include <opus.h>

int main()
{
    int error = OPUS_INVALID_STATE;

    OpusEncoder* encoder = opus_encoder_create(48000, 2, OPUS_APPLICATION_AUDIO, &error);
    AEDI_EXPECT(encoder != nullptr);
    AEDI_EXPECT(error == OPUS_OK);
    AEDI_EXPECT(opus_encoder_ctl(encoder, OPUS_SET_BITRATE(OPUS_AUTO)) == OPUS_OK);
    opus_encoder_destroy(encoder);

    OpusDecoder* decoder = opus_decoder_create(48000, 2, &error);
    AEDI_EXPECT(decoder != nullptr);
    AEDI_EXPECT(error == OPUS_OK);
    AEDI_EXPECT(opus_decoder_ctl(decoder, OPUS_SET_GAIN(0)) == OPUS_OK);
    opus_decoder_destroy(decoder);

    return 0;
}
