#include <wavpack/wavpack.h>

int main()
{
    AEDI_EXPECT(WavpackGetLibraryVersion() != 0);
    AEDI_EXPECT(WavpackGetLibraryVersionString() != nullptr);
    return 0;
}
