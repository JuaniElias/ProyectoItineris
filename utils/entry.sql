-- Insertar 5 pasajeros para el viaje con travel_id 17 (sin geocode, con uno 'Cancelado')
INSERT INTO itineris_traveler (segment_id, first_name, last_name, dni_type, dni, email, sex, date_of_birth, minor, nationality_id, phone, address_origin, geocode_origin, address_destination, geocode_destination, payment_status, paid_amount, refunded)
VALUES
    -- 1er pasajero: Viaja de Rosario a San Nicolás
    (161, 'Jorge', 'Ramírez', 'DNI', '32123456', 'jorge.ramirez@example.com', 'M', '1985-03-23', 0, 1, '341-555-1234',
    'Dr. Francisco Riva 1205, Rosario, Santa Fe', '-32.9835592,-60.6517199',
    'Pringles 648, San Nicolás, Buenos Aires', '-33.3466509,-60.2195207',  -- Dejar vacío el geocode
    'Confirmado', 7000, 0),

    -- 2do pasajero: Viaja de Rosario a Buenos Aires
    (162, 'Carla', 'Sosa', 'DNI', '29345678', 'carla.sosa@example.com', 'F', '1990-08-15', 0, 1, '341-555-5678',
    'JJ Valle 3865, Rosario, Santa Fe', '-32.9523912,-60.6840313',  -- Dejar vacío el geocode
    'Av. Corrientes 234, Buenos Aires, Buenos Aires', '-34.603196,-58.3732648',  -- Dejar vacío el geocode
    'Confirmado', 16300, 0),

    -- 3er pasajero: Viaja de San Nicolás a Buenos Aires
    (163, 'Rodrigo', 'Gómez', 'DNI', '33456789', 'rodrigo.gomez@example.com', 'M', '1980-12-05', 0, 1, '341-555-8765',
    'Rivadavia 123, San Nicolás de los Arroyos, Buenos Aires', '-33.337888,-60.2108306',  -- Dejar vacío el geocode
    'Av. Santa Fe 456, Lomas de Zamora, Buenos Aires', '-34.7522492,-58.4231905',  -- Dejar vacío el geocode
    'Confirmado', 9300, 0),

    -- 4to pasajero: Viaja de Rosario a San Nicolás (Cancelado)
    (161, 'Marta', 'López', 'DNI', '31123456', 'marta.lopez@example.com', 'F', '1978-04-17', 0, 1, '341-555-0987',
    'Av. Belgrano 321, Rosario, Santa Fe', '-32.9412866,-60.6374993',  -- Dejar vacío el geocode
    'Domingo Faustino Sarmiento 789, San Nicolás de los Arroyos, Buenos Aires', '-33.321846,-60.2586088',  -- Dejar vacío el geocode
    'Cancelado', 7000, 0),

    -- 5to pasajero: Viaja de San Nicolás a Buenos Aires
    (163, 'Luciana', 'Martínez', 'DNI', '29456789', 'luciana.martinez@example.com', 'F', '1992-11-30', 0, 1, '341-555-4567',
    'Av. Moreno 654, San Nicolás, Buenos Aires', '-33.3247478,-60.2418359',  -- Dejar vacío el geocode
    'Av. 9 de Julio 789, Buenos Aires, Buenos Aires', '-34.5961889,-58.3849036',  -- Dejar vacío el geocode
    'Confirmado', 9300, 0);

-- Notas:
-- nationality_id 1 es Argentina.
-- No se han asignado geocodes, ambos campos están vacíos según lo solicitado.
-- Un pasajero tiene el estado 'Cancelado'.
