#include <string.h>
#include <gme/gme.h>

int main()
{
    AEDI_EXPECT(gme_type_list() != nullptr);

    const gme_type_t type = gme_ay_type;
    const char* const type_system = "ZX Spectrum";
    const char* const type_ext = "AY";

    Music_Emu* emu = gme_new_emu(type, 44100);
    AEDI_EXPECT(emu != nullptr);
    AEDI_EXPECT(gme_warning(emu) == nullptr);

    AEDI_EXPECT(gme_type(emu) == type);
    AEDI_EXPECT(gme_type_multitrack(type) == 1);
    AEDI_EXPECT(strcmp(gme_type_system(type), type_system) == 0);
    AEDI_EXPECT(strcmp(gme_type_extension(type), type_ext) == 0);

    gme_delete(emu);
    return 0;
}
