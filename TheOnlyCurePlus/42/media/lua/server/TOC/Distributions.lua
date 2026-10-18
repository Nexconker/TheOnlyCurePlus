require('Items/Distributions')
require('Items/SuburbsDistributions')

-- TOC+: surgery tools, prostheses, crutches and the guide in the places that make sense.

local function add(listName, entries)
    local list = ProceduralDistributions and ProceduralDistributions.list and ProceduralDistributions.list[listName]
    if not list or not list.items then return end
    for i = 1, #entries, 2 do
        table.insert(list.items, entries[i])
        table.insert(list.items, entries[i + 1])
    end
end

local tourniquets = { "TOC.Surg_Arm_Tourniquet_L", 20, "TOC.Surg_Leg_Tourniquet_L", 12 }

add("MedicalClinicTools", { "TOC.BoneSaw", 4, "TOC.SurgicalKit", 1, "TOC.Crutch", 5, "TOC.FieldSurgeryGuide", 3,
    "TOC.Prost_BaseScrap_L", 2, "TOC.Prost_HeadHook_L", 3, "TOC.Prost_BaseMech_L", 2, "TOC.Prost_HeadMechHand_L", 2, "TOC.Prost_BaseMed_L", 1, "TOC.Prost_HeadMedHand_L", 1,
    "TOC.Prost_PegLeg_L", 1, "TOC.Prost_MechLeg_L", 1, "TOC.Prost_MedicalLeg_L", 1,
    "TOC.Surg_Arm_Tourniquet_L", 20, "TOC.Surg_Leg_Tourniquet_L", 12 })
add("MedicalStorageTools", { "TOC.BoneSaw", 6, "TOC.SurgicalKit", 2, "TOC.Crutch", 8, "TOC.Surg_Arm_Tourniquet_L", 15, "TOC.Surg_Leg_Tourniquet_L", 10 })
add("HospitalLockers", { "TOC.Crutch", 10, "TOC.Prost_BaseMed_L", 2, "TOC.Prost_HeadMedHand_L", 2, "TOC.Prost_MedicalLeg_L", 2, "TOC.Surg_Arm_Tourniquet_L", 10, "TOC.Surg_Leg_Tourniquet_L", 8 })
add("HospitalRoomWardrobe", { "TOC.Crutch", 6, "TOC.Prost_MedicalLeg_L", 1 })
add("AmbulanceDriverTools", { "TOC.Surg_Arm_Tourniquet_L", 20, "TOC.Surg_Leg_Tourniquet_L", 15, "TOC.BoneSaw", 2 })
add("DoctorTools", { "TOC.Surg_Arm_Tourniquet_L", 10, "TOC.FieldSurgeryGuide", 2, "TOC.BoneSaw", 2 })
add("NurseTools", { "TOC.Surg_Arm_Tourniquet_L", 10, "TOC.FieldSurgeryGuide", 1 })
add("ArmyBunkerMedical", { "TOC.Surg_Arm_Tourniquet_L", 20, "TOC.Surg_Leg_Tourniquet_L", 15, "TOC.BoneSaw", 4, "TOC.SurgicalKit", 2, "TOC.FieldSurgeryGuide", 4 })
add("ArmyStorageMedical", { "TOC.Surg_Arm_Tourniquet_L", 20, "TOC.Surg_Leg_Tourniquet_L", 15, "TOC.BoneSaw", 4, "TOC.SurgicalKit", 2 })
add("MedicalOfficeBooks", { "TOC.FieldSurgeryGuide", 4 })
add("HospitalMagazineRack", { "TOC.FieldSurgeryGuide", 3 })
add("BookstoreMedical", { "TOC.FieldSurgeryGuide", 4 })
add("LibraryMedical", { "TOC.FieldSurgeryGuide", 4 })
add("UniversityLibraryMedical", { "TOC.FieldSurgeryGuide", 4 })
add("SafehouseMedical", { "TOC.Surg_Arm_Tourniquet_L", 6, "TOC.Crutch", 2 })
