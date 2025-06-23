-- =========================
-- Hospital Appointment Management Sample Database
-- =========================

-- 1. Departments
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

INSERT INTO departments (name) VALUES
('Cardiology'),
('Neurology'),
('Pediatrics'),
('Orthopedics'),
('General Medicine');

-- 2. Subdivisions
CREATE TABLE subdivisions (
    id SERIAL PRIMARY KEY,
    department_id INTEGER REFERENCES departments(id),
    name VARCHAR(100) NOT NULL
);

INSERT INTO subdivisions (department_id, name) VALUES
(1, 'Interventional Cardiology'),
(1, 'Non-Invasive Cardiology'),
(2, 'Stroke'),
(2, 'Epilepsy'),
(3, 'Neonatology'),
(3, 'Pediatric Oncology'),
(4, 'Sports Medicine'),
(4, 'Joint Replacement'),
(5, 'Internal Medicine'),
(5, 'Family Medicine');

-- 3. Doctors
CREATE TABLE doctors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    subdivision_id INTEGER REFERENCES subdivisions(id),
    profile TEXT,
    tags TEXT[]
);

INSERT INTO doctors (name, department_id, subdivision_id, profile, tags) VALUES
('Dr. Alice Smith', 1, 1, 'Expert in heart catheterization and stent placement.', ARRAY['angioplasty', 'stents', 'heart attack']),
('Dr. Bob Johnson', 1, 2, 'Specialist in echocardiography and heart failure.', ARRAY['echocardiogram', 'heart failure', 'hypertension']),
('Dr. Carol Lee', 2, 3, 'Renowned for acute stroke management.', ARRAY['stroke', 'thrombolysis', 'TIA']),
('Dr. David Kim', 2, 4, 'Epilepsy specialist with 10 years experience.', ARRAY['epilepsy', 'seizures', 'EEG']),
('Dr. Eva Brown', 3, 5, 'Neonatologist focusing on premature infants.', ARRAY['premature', 'NICU', 'newborn']),
('Dr. Frank Green', 3, 6, 'Pediatric oncologist with expertise in leukemia.', ARRAY['leukemia', 'chemotherapy', 'child cancer']),
('Dr. Grace White', 4, 7, 'Sports medicine doctor for athletic injuries.', ARRAY['sports injury', 'rehabilitation', 'ACL']),
('Dr. Henry Black', 4, 8, 'Joint replacement surgeon.', ARRAY['hip replacement', 'knee replacement', 'arthritis']),
('Dr. Irene Young', 5, 9, 'Internal medicine specialist for chronic diseases.', ARRAY['diabetes', 'hypertension', 'cholesterol']),
('Dr. Jack King', 5, 10, 'Family medicine doctor for all ages.', ARRAY['family care', 'preventive', 'checkup']),
('Dr. Karen Adams', 1, 1, 'Interventional cardiologist with 15 years experience.', ARRAY['angioplasty', 'stents', 'arrhythmia']),
('Dr. Liam Scott', 1, 2, 'Non-invasive cardiologist, expert in heart imaging.', ARRAY['echocardiogram', 'stress test', 'hypertension']),
('Dr. Mia Turner', 2, 3, 'Stroke specialist, rapid response team leader.', ARRAY['stroke', 'clot retrieval', 'TIA']),
('Dr. Noah Walker', 2, 4, 'Epileptologist, pediatric and adult.', ARRAY['epilepsy', 'seizures', 'EEG']),
('Dr. Olivia Harris', 3, 5, 'Neonatologist, expert in respiratory distress.', ARRAY['premature', 'ventilation', 'NICU']),
('Dr. Paul Lewis', 3, 6, 'Pediatric oncologist, solid tumors.', ARRAY['tumor', 'chemotherapy', 'child cancer']),
('Dr. Quinn Hall', 4, 7, 'Sports medicine, musculoskeletal injuries.', ARRAY['sports injury', 'muscle tear', 'rehabilitation']),
('Dr. Rachel Allen', 4, 8, 'Joint replacement, minimally invasive surgery.', ARRAY['hip replacement', 'knee replacement', 'arthroscopy']),
('Dr. Samuel Wright', 5, 9, 'Internal medicine, metabolic disorders.', ARRAY['diabetes', 'thyroid', 'cholesterol']),
('Dr. Tina Baker', 5, 10, 'Family medicine, women''s health.', ARRAY['family care', 'women health', 'preventive']),
('Dr. Umar Patel', 1, 1, 'Interventional cardiologist, arrhythmia management.', ARRAY['arrhythmia', 'pacemaker', 'angioplasty']),
('Dr. Vera Clark', 1, 2, 'Non-invasive cardiologist, hypertension specialist.', ARRAY['hypertension', 'heart failure', 'ECG']),
('Dr. Will Evans', 2, 3, 'Stroke neurologist, post-stroke rehab.', ARRAY['stroke', 'rehabilitation', 'TIA']),
('Dr. Xena Foster', 2, 4, 'Epilepsy, pediatric focus.', ARRAY['epilepsy', 'child neurology', 'seizures']),
('Dr. Yusuf Grant', 3, 5, 'Neonatologist, infection control.', ARRAY['NICU', 'infection', 'premature']),
('Dr. Zoe Hill', 3, 6, 'Pediatric oncology, brain tumors.', ARRAY['brain tumor', 'chemotherapy', 'child cancer']),
('Dr. Alan Reed', 4, 7, 'Sports medicine, orthopedic trauma.', ARRAY['sports injury', 'fracture', 'rehabilitation']),
('Dr. Bella Price', 4, 8, 'Joint replacement, elderly care.', ARRAY['hip replacement', 'arthritis', 'elderly']),
('Dr. Carl Stone', 5, 9, 'Internal medicine, infectious diseases.', ARRAY['infection', 'fever', 'chronic disease']),
('Dr. Dana West', 5, 10, 'Family medicine, adolescent care.', ARRAY['family care', 'adolescent', 'preventive']),
('Dr. Ethan Young', 1, 1, 'Interventional cardiologist, heart failure.', ARRAY['heart failure', 'angioplasty', 'stents']),
('Dr. Fiona Zane', 1, 2, 'Non-invasive cardiologist, ECG expert.', ARRAY['ECG', 'hypertension', 'heart checkup']),
('Dr. George Adams', 2, 3, 'Stroke, neuroimaging.', ARRAY['stroke', 'MRI', 'TIA']),
('Dr. Hannah Brown', 2, 4, 'Epilepsy, EEG monitoring.', ARRAY['epilepsy', 'EEG', 'seizures']),
('Dr. Ian Carter', 3, 5, 'Neonatology, jaundice management.', ARRAY['jaundice', 'NICU', 'premature']),
('Dr. Julia Davis', 3, 6, 'Pediatric oncology, leukemia.', ARRAY['leukemia', 'chemotherapy', 'child cancer']),
('Dr. Kevin Edwards', 4, 7, 'Sports medicine, ligament injuries.', ARRAY['ligament', 'sports injury', 'rehabilitation']),
('Dr. Laura Fisher', 4, 8, 'Joint replacement, knee specialist.', ARRAY['knee replacement', 'arthroscopy', 'arthritis']),
('Dr. Mark Garcia', 5, 9, 'Internal medicine, hypertension.', ARRAY['hypertension', 'cholesterol', 'diabetes']),
('Dr. Nina Harris', 5, 10, 'Family medicine, geriatric care.', ARRAY['family care', 'elderly', 'preventive']),
('Dr. Oscar Ingram', 1, 1, 'Interventional cardiology, complex cases.', ARRAY['angioplasty', 'stents', 'arrhythmia']),
('Dr. Priya Joshi', 1, 2, 'Non-invasive cardiology, preventive care.', ARRAY['preventive', 'hypertension', 'heart checkup']),
('Dr. Quentin Knight', 2, 3, 'Stroke, rehabilitation.', ARRAY['stroke', 'rehabilitation', 'TIA']),
('Dr. Rita Lee', 2, 4, 'Epilepsy, adult focus.', ARRAY['epilepsy', 'seizures', 'EEG']),
('Dr. Steve Martin', 3, 5, 'Neonatology, nutrition.', ARRAY['nutrition', 'NICU', 'premature']),
('Dr. Tara Nelson', 3, 6, 'Pediatric oncology, lymphoma.', ARRAY['lymphoma', 'chemotherapy', 'child cancer']),
('Dr. Umar O''Brien', 4, 7, 'Sports medicine, pediatric injuries.', ARRAY['sports injury', 'child', 'rehabilitation']),
('Dr. Vicky Patel', 4, 8, 'Joint replacement, hip specialist.', ARRAY['hip replacement', 'arthroscopy', 'arthritis']),
('Dr. Walter Quinn', 5, 9, 'Internal medicine, respiratory diseases.', ARRAY['asthma', 'COPD', 'chronic disease']),
('Dr. Xander Ross', 5, 10, 'Family medicine, vaccination.', ARRAY['family care', 'vaccination', 'preventive']),
('Dr. Yara Singh', 1, 1, 'Interventional cardiology, pediatric cases.', ARRAY['pediatric', 'angioplasty', 'stents']),
('Dr. Zane Taylor', 1, 2, 'Non-invasive cardiology, ECG and imaging.', ARRAY['ECG', 'imaging', 'hypertension']);

-- 4. Doctor Availability
CREATE TABLE doctor_availability (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER REFERENCES doctors(id),
    date DATE NOT NULL,
    time_slot VARCHAR(20) NOT NULL,
    is_booked BOOLEAN DEFAULT FALSE
);

-- Doctor availability for 50 doctors, 3 slots per day for 3 days
do
$$
declare
    d integer;
    day_offset integer;
    slot text[] := array['09:00-09:30', '10:00-10:30', '11:00-11:30'];
    s integer;
begin
    for d in 1..50 loop
        for day_offset in 0..2 loop
            for s in 1..3 loop
                insert into doctor_availability (doctor_id, date, time_slot)
                values (d, current_date + day_offset, slot[s]);
            end loop;
        end loop;
    end loop;
end;
$$;

-- 5. Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    contact_info VARCHAR(100)
);

-- 6. Appointments
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    doctor_id INTEGER REFERENCES doctors(id),
    date DATE NOT NULL,
    time_slot VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'booked'
); 