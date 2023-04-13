#include <xmp.h>

int main()
{
    xmp_context context = xmp_create_context();
    AEDI_EXPECT(context != nullptr);
    AEDI_EXPECT(xmp_syserrno() == 0);
    xmp_free_context(context);

    return 0;
}
