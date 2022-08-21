#include <SDL_net.h>

int main()
{
    AEDI_EXPECT(SDLNet_Init() == 0);
    SDLNet_Quit();

    return 0;
}
