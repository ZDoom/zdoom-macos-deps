#include <mpg123.h>

int main(int argc, char **argv)
{
    if (mpg123_init() != MPG123_OK)
    {
        return 1;
    }

    mpg123_handle* mh = mpg123_new(NULL, NULL);

    if (mh == nullptr)
    {
        return 1;
    }

    if (mpg123_param(mh, MPG123_VERBOSE, 1, 0.) != MPG123_OK)
    {
        return 1;
    }

    mpg123_delete(mh);
    mpg123_exit();

    return 0;
}
