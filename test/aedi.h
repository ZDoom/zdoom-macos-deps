#define AEDI_EXPECT(CODE) if (!(CODE)) { puts(#CODE); return 1; }

extern "C" int puts(const char*);
