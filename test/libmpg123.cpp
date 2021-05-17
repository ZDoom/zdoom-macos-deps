#include <mpg123.h>

int main(int argc, char **argv)
{
    AEDI_EXPECT(mpg123_init() == MPG123_OK);

    mpg123_handle* mh = mpg123_new(NULL, NULL);
    AEDI_EXPECT(mh != nullptr);
    AEDI_EXPECT(mpg123_param(mh, MPG123_VERBOSE, 1, 0.) == MPG123_OK);

    mpg123_delete(mh);
    mpg123_exit();

    return 0;
}
