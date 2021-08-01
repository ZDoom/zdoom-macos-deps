#include <brotli/decode.h>

int main()
{
    BrotliDecoderState* decoder = BrotliDecoderCreateInstance(nullptr, nullptr, nullptr);
    AEDI_EXPECT(decoder != nullptr);
    AEDI_EXPECT(BrotliDecoderSetParameter(decoder, BROTLI_DECODER_PARAM_LARGE_WINDOW, 1) == BROTLI_TRUE);
    BrotliDecoderDestroyInstance(decoder);

    return 0;
}
