#include <string.h>
#include <glib.h>

int main()
{
    const char reference[] = "Test 123!@#";
    const size_t length = strlen(reference);

    gchar* const utf8 = g_convert(reference, sizeof reference - 1, "ascii", "utf-8", nullptr, nullptr, nullptr);
    AEDI_EXPECT(utf8 != nullptr);

    gchar* const ascii = g_convert(utf8, strlen(utf8), "utf-8", "ascii", nullptr, nullptr, nullptr);
    AEDI_EXPECT(ascii != nullptr);
    g_free(utf8);

    AEDI_EXPECT(strcmp(reference, ascii) == 0);
    g_free(ascii);

    return 0;
}
