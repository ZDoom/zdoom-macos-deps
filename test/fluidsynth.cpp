#include <fluidsynth.h>

#include <stdio.h>

int main()
{
    AEDI_EXPECT(fluid_version_str() != nullptr);

    fluid_settings_t* settings = new_fluid_settings();
    AEDI_EXPECT(settings != nullptr);

    fluid_synth_t* synth = new_fluid_synth(settings);
    AEDI_EXPECT(synth != nullptr);

    delete_fluid_synth(synth);
    delete_fluid_settings(settings);
}
