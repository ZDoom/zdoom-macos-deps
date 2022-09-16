#include <vorbis/vorbisenc.h>

int main()
{
    vorbis_info info;
    vorbis_info_init(&info);

    AEDI_EXPECT(vorbis_encode_setup_managed(&info, 2, 44100, -1, 128 * 1024, -1) == 0);
    AEDI_EXPECT(vorbis_encode_ctl(&info, OV_ECTL_RATEMANAGE2_SET, nullptr) == 0);
    AEDI_EXPECT(vorbis_encode_setup_init(&info) == 0);

    vorbis_info_clear(&info);

    return 0;
}
