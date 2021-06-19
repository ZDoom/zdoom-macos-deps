#include <unistd.h>
#include <tiffio.h>

int main(int argc, char* argv[])
{
    const char* const filename = "test.tiff";
    TIFF* f = TIFFOpen(filename, "w");
    AEDI_EXPECT(f != nullptr);

    AEDI_EXPECT(TIFFSetField(f, TIFFTAG_IMAGEWIDTH, 32) == 1);
    AEDI_EXPECT(TIFFSetField(f, TIFFTAG_IMAGEWIDTH, 32) == 1);

    TIFFClose(f);
    AEDI_EXPECT(unlink(filename) == 0);

    return 0;
}
