#include <brotli/encode.h>

int main()
{
    BrotliEncoderState* encoder = BrotliEncoderCreateInstance(nullptr, nullptr, nullptr);
    AEDI_EXPECT(encoder != nullptr);
    AEDI_EXPECT(BrotliEncoderSetParameter(encoder, BROTLI_PARAM_LARGE_WINDOW, 1) == BROTLI_TRUE);
    BrotliEncoderDestroyInstance(encoder);

    return 0;
}
