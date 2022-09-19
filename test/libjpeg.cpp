#include <stdio.h>
#include <jpeglib.h>

int main()
{
    jpeg_compress_struct compress = {};
    jpeg_create_compress(&compress);

    compress.input_components = 3;
    jpeg_set_defaults(&compress);

    compress.in_color_space = JCS_EXT_RGB;
    jpeg_default_colorspace(&compress);

    jpeg_destroy_compress(&compress);

    jpeg_decompress_struct decompress = {};
    jpeg_create_decompress(&decompress);
    jpeg_destroy_decompress(&decompress);

    return 0;
}
