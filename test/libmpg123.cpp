#include <mpg123.h>

int main(int argc, char **argv)
{
    mpg123_init();
    mpg123_handle* mh = mpg123_new(NULL, NULL);
    mpg123_param(mh, MPG123_VERBOSE, 1, 0.);
    mpg123_delete(mh);
    mpg123_exit();
    return 0;
}
