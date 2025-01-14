#include <png.h>

int main()
{
    png_structp png = png_create_write_struct(PNG_LIBPNG_VER_STRING, nullptr, nullptr, nullptr);
    AEDI_EXPECT(png != nullptr);

    png_destroy_write_struct(&png, nullptr);
    return 0;
}
