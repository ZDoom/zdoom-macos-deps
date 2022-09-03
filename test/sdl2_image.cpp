#include <SDL_image.h>

int main()
{
    AEDI_EXPECT(IMG_Init(0) == 0);
    IMG_Quit();

    return 0;
}
