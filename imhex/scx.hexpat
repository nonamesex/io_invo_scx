#pragma pattern_limit 2147483647

import std.string;
import std.mem;

bitfield SCX3MaterialFlags {
    bool alphaOpacity: 1; // 0x1
    bool vertexColorBlend: 1; // 0x2
    padding: 4;
    bool layer2BlendByAlpha: 1; // 0x40
    padding: 1;
    bool diffuseBlend: 1; // 0x100
    padding: 3;
    bool layer2VertexColorBlend: 1; // 0x1000
    padding: 19;
};

struct SCX3Material {
    u32 size;

    if (size == 0) {
        return;
    }

    float diffuseColor[3];
    float diffuseOpacity;

    float specularColor[3];
    float specularWeight;
    float glossinesWeight;

    SCX3MaterialFlags flags;

    u16 diffuseMapIndex;
    u16 bumpMapIndex;
    u16 specularMapIndex;
    u16 reflectionMapIndex;
    u16 diffuseLayer2MapIndex;
    u16 unk05MapIndex;

    if (size > 56) {
        u16 illuminationMapIndex;
        u16 unk07MapIndex;

        u32 vertexSize;

        u32 unk01;
        u16 unk02;

        u16 diffuseMix1MapChannel;
        u16 diffuseMix2MapChannel;
        u16 bumpMapChannel;
        u16 specularMapChannel;

        u16 unk07;
        u32 unk08;
        u32 unk09;
        u32 unk10;

        float illuminationColor[3];
    }

    if (size > 104) {
        char materialName[32];
    }
} [[single_color]];

struct SCX3VertexData {
    float position[3];
    float normal[3];

    float uv1[2];
    float uv2[2];

    u8 color[4]; //BGRA

    if (parent.material.size > 56) {
        u32 unk01;
        u32 unk02;

        float uv3[2];

        u32 unk03;
    }
};

struct SCX3ModelDef {
    std::print("{}", $);
    SCX3Material material;
    u32 vertexCount;
    SCX3VertexData vertexData[vertexCount] [[single_color]];
    u32 faceCount;
    u32 indices[faceCount * 3];
} [[single_color]];

enum SCX4EntryType : u32 {
    MaterialDef = 0,  //MaterialV4
    HardSurfaceDef = 1,  //HardSurfaceDef
    SparseBoneIndexList = 2,  //BoneList
    BoneIndexList = 3,  //BoneList
    VertexData = 4,  //VertexDataV4
    FaceIndices = 5  //FaceDef
};

enum SCX4MaterialEntryType : u32 {
    DiffuseColor = 0x00000000,
    SpecularColor = 0x00000001,
    EmissiveColor = 0x00000002,
    SpecularIntensity = 0x01000000,
    ReflectionIntensity = 0x01000001,
    BumpIntensity = 0x01000002,
    DiffuseMap = 0x06000000,
    DiffuseMixSecond = 0x06000001,
    BumpMap = 0x06000002,
    ReflectionMap = 0x06000003,
    EmissiveMap = 0x06000004,
    MaterialName = 0x08000000
};

enum SCX4MapTillingFlags : u32 {
    UMirrorVMirror = 0x0,
    UTileVTile = 0x3
};

struct SCX4MaterialMapDef {
    u32 textureIndex;
    u32 mapChannel;
    SCX4MapTillingFlags tillingFlags;
    float tillingU;
    float tillingV;
    float offsetU;
    float offsetV;
};

struct SCX4MaterialEntry {
    SCX4MaterialEntryType materialEntryType;

    if (materialEntryType == SCX4MaterialEntryType::MaterialName) {
        char materialName[32];
    } else if (
        materialEntryType == SCX4MaterialEntryType::DiffuseColor
        || materialEntryType == SCX4MaterialEntryType::SpecularColor
        || materialEntryType == SCX4MaterialEntryType::EmissiveColor) {
        u8 color[4]; // RGBA
    } else if (
        materialEntryType == SCX4MaterialEntryType::SpecularIntensity
        || materialEntryType == SCX4MaterialEntryType::ReflectionIntensity
        || materialEntryType == SCX4MaterialEntryType::BumpIntensity) {
        float intensity;
    } else if (
        materialEntryType == SCX4MaterialEntryType::DiffuseMap
        || materialEntryType == SCX4MaterialEntryType::DiffuseMixSecond
        || materialEntryType == SCX4MaterialEntryType::BumpMap
        || materialEntryType == SCX4MaterialEntryType::ReflectionMap
        || materialEntryType == SCX4MaterialEntryType::EmissiveMap) {
        SCX4MaterialMapDef mapDef;
    }
} [[single_color]];

struct SCX4Material {
    SCX4EntryType type;
    u32 size;
    u32 flags;
    u32 unk4;
    u32 entriesCount;

    SCX4MaterialEntry materialEntry[entriesCount];
} [[single_color]];

struct SCX4HardSurface {
    SCX4EntryType type;
    u32 size;
    u32 unk3;
} [[single_color]];

bitfield SCX4VertexType {
    bool Position: 1; // 0x1
    bool BoneWeight0: 1; // 0x2
    bool BoneWeight1: 1; // 0x4
    bool BoneWeight2: 1; // 0x8
    bool BoneWeight3: 1; // 0x10
    bool BoneIndRef: 1; // 0x20
    bool Normal: 1; // 0x40
    bool VertexEmissive: 1; // 0x80
    bool VertexColor: 1; // 0x100
    bool UV1: 1; // 0x200
    bool UV2: 1; // 0x400
    bool UV3: 1; // 0x800
    padding: 6;
    bool BumpMapNormal: 1; // 0x40000
    padding: 13;
};

struct SCX4VertexData {
    if (parent.vertexType.Position) float position[3];
    if (parent.vertexType.BoneWeight0) float weight0;
    if (parent.vertexType.BoneWeight1) float weight1;
    if (parent.vertexType.BoneWeight2) float weight2;
    if (parent.vertexType.BoneWeight3) float weight3;
    if (parent.vertexType.BoneIndRef) u8 boneIndRef[4];
    if (parent.vertexType.Normal) float normal[3];
    if (parent.vertexType.VertexEmissive) u8 emissiveColor[4];
    if (parent.vertexType.VertexColor) u8 vertexColor[4];
    if (parent.vertexType.UV1) float uv1[2];
    if (parent.vertexType.UV2) float uv2[2];
    if (parent.vertexType.UV3) float uv3[2];
    if (parent.vertexType.BumpMapNormal) float bumpMapNormal[3];
};

struct SCX4Vertices {
    SCX4EntryType type;
    u32 size;
    u32 verticesCount;
    SCX4VertexType vertexType;
    SCX4VertexData vertexData[verticesCount];
} [[single_color]];

struct SCX4FaceIndices {
    SCX4EntryType type;
    u32 size;
    u32 facesCount;
    u16 indices[facesCount];
} [[single_color]];

struct SCX4Header {
    SCX4EntryType entryType;
    u32 entryOffset;

    if (entryType == SCX4EntryType::MaterialDef) {
        SCX4Material material @ entryOffset;
    } else if (entryType == SCX4EntryType::HardSurfaceDef) {
        SCX4HardSurface hardSurface @ entryOffset;
    } else if (entryType == SCX4EntryType::VertexData) {
        SCX4Vertices vertexData @ entryOffset;
    } else if (entryType == SCX4EntryType::FaceIndices) {
        SCX4FaceIndices faceIndices @ entryOffset;
    } else {
        u32 data @ entryOffset;
    }
} [[single_color]];

struct InvictusSCX {
    char magic[4];
    u32 version;

    if (version == 3) {
        SCX3ModelDef model[while (!std::mem::eof())];
    } else if (version == 4) {
        u32 headerEntriesCount;
        SCX4Header headerEntries[headerEntriesCount];
    }
};

InvictusSCX scx @ 0x0;
