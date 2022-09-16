#include <vorbis/codec.h>

int main()
{
    vorbis_info info;
    vorbis_info_init(&info);
    vorbis_info_clear(&info);

    vorbis_comment comment;
    vorbis_comment_init(&comment);
    vorbis_comment_add(&comment, "content");
    vorbis_comment_clear(&comment);

    return 0;
}
