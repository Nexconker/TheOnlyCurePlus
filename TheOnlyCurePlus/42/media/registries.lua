_TOCRegistries = {}

_TOCRegistries.traits = {
    Amputee_Hand = CharacterTrait.register("toc:amputee_hand"),
    Amputee_ForeArm = CharacterTrait.register("toc:amputee_forearm"),
    Amputee_UpperArm = CharacterTrait.register("toc:amputee_upperarm"),
    -- TOC+: right side and legs
    Amputee_Hand_R = CharacterTrait.register("toc:amputee_hand_r"),
    Amputee_ForeArm_R = CharacterTrait.register("toc:amputee_forearm_r"),
    Amputee_UpperArm_R = CharacterTrait.register("toc:amputee_upperarm_r"),
    Amputee_Foot = CharacterTrait.register("toc:amputee_foot"),
    Amputee_LowerLeg = CharacterTrait.register("toc:amputee_lowerleg"),
    Amputee_Foot_R = CharacterTrait.register("toc:amputee_foot_r"),
    Amputee_LowerLeg_R = CharacterTrait.register("toc:amputee_lowerleg_r"),
}

_TOCRegistries.bodylocations = {
    TOC_Arm_L = ItemBodyLocation.register("toc:Arm_L"),
    TOC_Arm_R = ItemBodyLocation.register("toc:Arm_R"),
    TOC_ArmProst_L = ItemBodyLocation.register("toc:ArmProst_L"),
    TOC_ArmProst_R = ItemBodyLocation.register("toc:ArmProst_R"),
    -- TOC+ 3.3: cabezal de la prótesis modular (mano, gancho, motosierra...), encima de la base (toc:ArmProst_X)
    TOC_ArmHead_L = ItemBodyLocation.register("toc:ArmHead_L"),
    TOC_ArmHead_R = ItemBodyLocation.register("toc:ArmHead_R"),
    TOC_ArmAccessory_L = ItemBodyLocation.register("toc:ArmAccessory_L"),
    TOC_ArmAccessory_R = ItemBodyLocation.register("toc:ArmAccessory_R"),
    -- TOC+: legs
    TOC_Leg_L = ItemBodyLocation.register("toc:Leg_L"),
    TOC_Leg_R = ItemBodyLocation.register("toc:Leg_R"),
    TOC_LegProst_L = ItemBodyLocation.register("toc:LegProst_L"),
    TOC_LegProst_R = ItemBodyLocation.register("toc:LegProst_R"),
    TOC_LegAccessory_L = ItemBodyLocation.register("toc:LegAccessory_L"),
    TOC_LegAccessory_R = ItemBodyLocation.register("toc:LegAccessory_R"),
}
