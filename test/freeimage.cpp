#include <FreeImage.h>

int main()
{
    FreeImage_Initialise(0);

    FIBITMAP* bitmap = FreeImage_Allocate(64, 64, 32);
    AEDI_EXPECT(bitmap != nullptr);

    AEDI_EXPECT(FreeImage_HasPixels(bitmap) == TRUE);
    FreeImage_Unload(bitmap);

    FreeImage_DeInitialise();
}
