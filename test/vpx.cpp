#include <vpx/vpx_decoder.h>
#include <vpx/vp8dx.h>

int main()
{
    vpx_codec_ctx_t1 codec;

    if (vpx_codec_dec_init(&codec, &vpx_codec_vp8_dx_algo, nullptr, 0) != VPX_CODEC_OK)
    {
        return 1;
    }

    vp8_postproc_cfg_t pp = { 0, 0, 0 };

    if (vpx_codec_control(&codec, VP8_SET_POSTPROC, &pp) != VPX_CODEC_OK)
    {
        return 1;
    }

    if (vpx_codec_destroy(&codec) != VPX_CODEC_OK)
    {
        return 1;
    }

    return 0;
}
