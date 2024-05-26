close all
clear
clc

file = uigetfile('./*.mat');
raw = load(file);

clean = raw.raw;
firstClean = find(raw.crc == 0,1);
for i = 1:(firstClean-1)
    clean(i,:) = clean(firstClean,:);
end
crcIdx = find(raw.crc);
crcIdx(crcIdx < firstClean) = [];
for i = 1:length(crcIdx)
    clean(crcIdx,:) = clean(crcIdx-1,:);
end

data = clean(:,1:64);

figure
plot(data)