#include <ft2build.h>
#include FT_FREETYPE_H

int main()
{
    FT_Library library;
    AEDI_EXPECT(FT_Init_FreeType(&library) == FT_Err_Ok);
    AEDI_EXPECT(FT_Done_FreeType(library) == FT_Err_Ok);

    return 0;
}
